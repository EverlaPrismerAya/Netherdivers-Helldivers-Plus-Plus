-- HD2-Addon: mods/netherdivers/plas15
local behavior = {}

function behavior.new()
    return { started = nil, warning = false, result = nil, magazine_clear_required = false }
end

function behavior.tick(state, now, unsafe, trigger_down)
    if not unsafe then
        state.started, state.warning, state.result, state.magazine_clear_required = nil, false, nil, false
        return state
    end
    if trigger_down and not state.started then
        state.started, state.warning, state.result, state.magazine_clear_required = now, false, nil, false
    end
    if state.started and trigger_down then
        local elapsed = now - state.started
        state.warning = elapsed >= 4.0
        state.result = elapsed >= 4.5 and 'penalty' or elapsed >= 4.0 and 'overcharge' or nil
        state.magazine_clear_required = elapsed >= 4.0
    elseif state.started and not trigger_down then
        local elapsed = now - state.started
        state.result = state.result == 'penalty' and 'penalty' or elapsed >= 4.5 and 'penalty'
            or elapsed >= 4.0 and 'overcharge' or 'vanilla'
        state.magazine_clear_required = elapsed >= 4.0
        state.started, state.warning = nil, false
    end
    return state
end

_G.NetherdiversPlas15Behavior = behavior

local ok, hd2 = pcall(require, 'mods/skyeshade/hd2runtime')
if not ok or not hd2 then return end

local mod = hd2.mod()
local EXPECTED_EXE = 'F5FEE03DCFDB2E553A4752C283590950AC13316B376D8196AA556FF0400D5F06'
local EXPECTED_DLL = '2E2C3B7C2500646DADD5F2B4C6E0504DBB7E7896139F64CDDC0D1813C718F51E'
local PLAS15 = '0xAA69A60D74A3EC54'
local EPOCH_WARNING = 3972604218
local DEFAULT_OVERCHARGE = 161
local FIRE_MODE_SAFETY_OFF = 4
local FIREMODE_SELECTOR = 3
local PLAS15_PROJECTILE = 171
local PLAS15_CHARGE_MEDIUM = 70
local PLAS15_CHARGE = 341
local PLAS15_DAMAGE = 56
local PLAS15_IMPACT = 355
local PLAS15_IMPACT_DAMAGE = 305
local OVERCHARGE_DAMAGE = 234

local function find_candidate(catalog, resource)
    for _, candidate in ipairs(catalog.candidates) do
        if candidate.resourceHash == resource then return candidate end
    end
    error('PLAS15_RESOURCE_NOT_FOUND: ' .. resource)
end

local function record_value(bytes, offset, kind)
    local b = require('hd2runtime/core/bytes')
    return b.value(bytes, offset, kind)
end

local function same_number(actual, expected)
    return actual == expected or (type(actual) == 'number' and type(expected) == 'number'
        and math.abs(actual - expected) < 0.0001)
end

local function matches_expected(actual, expected)
    if type(expected) ~= 'table' then return same_number(actual, expected) end
    for _, candidate in ipairs(expected) do
        if same_number(actual, candidate) then return true end
    end
    return false
end

local function add_change(changes, record, offset, kind, expected, value, label)
    local actual = record_value(record.bytes, offset, kind)
    assert(matches_expected(actual, expected) or same_number(actual, value),
        'PLAS15_CONFLICT: ' .. label .. ' is ' .. tostring(actual))
    if not same_number(actual, value) then
        changes[#changes + 1] = { record = record, offset = offset, kind = kind,
            before = actual, value = value, label = label }
    end
end

local function apply_changes(runtime, reader, changes)
    if #changes == 0 then return end
    local bytes = require('hd2runtime/core/bytes')
    local pages = {}
    for _, change in ipairs(changes) do
        local address = change.record.owner.base + change.record.offset + change.offset
        change.address = address
        change.before_bytes = reader.read(change.record.owner, change.record.offset + change.offset,
            change.kind == 'u8' and 1 or 4, true)
        change.after_bytes = bytes.encode(change.value, change.kind)
        pages[address - address % 4096] = true
    end
    local opened = {}
    local written = {}
    local ok, reason = pcall(function()
        for page in pairs(pages) do
            local region = assert(runtime.query(page), 'PLAS15_PAGE_QUERY_FAILED')
            assert(region.base == page and region.protect == 2, 'PLAS15_PAGE_GUARD_FAILED')
            local previous = assert(runtime.protect(page, 4096, 4), 'PLAS15_PAGE_OPEN_FAILED')
            opened[page] = previous
        end
        for _, change in ipairs(changes) do
            local wrote, error_code, count = runtime.write(change.address, change.after_bytes)
            assert(wrote and count == #change.after_bytes,
                'PLAS15_WRITE_FAILED:' .. tostring(error_code))
            written[#written + 1] = change
            assert(runtime.read(change.address, #change.after_bytes) == change.after_bytes,
                'PLAS15_READBACK_FAILED: ' .. change.label)
        end
    end)
    if not ok then
        for index = #written, 1, -1 do
            local change = written[index]
            runtime.write(change.address, change.before_bytes)
            assert(runtime.read(change.address, #change.before_bytes) == change.before_bytes,
                'PLAS15_ROLLBACK_FAILED: ' .. change.label)
        end
    end
    for page, previous in pairs(opened) do
        assert(runtime.protect(page, 4096, previous), 'PLAS15_PAGE_RESTORE_FAILED')
    end
    if not ok then error(reason) end
end

local function patch_native()
    local writer = require('hd2runtime/runtime/windows_write')
    local runtime = writer.create()
    local profile = require('hd2runtime/schemas/current')
    local reader = require('hd2runtime/runtime/reader').new(runtime)
    local discover = require('hd2runtime/runtime/discover')
    local catalog_module = require('hd2runtime/core/entity_catalog')
    local b = require('hd2runtime/core/bytes')

    local exe = assert(runtime.module('helldivers2.exe'), 'PLAS15_EXE_NOT_LOADED')
    local dll = assert(runtime.module('game.dll'), 'PLAS15_DLL_NOT_LOADED')
    assert(runtime.module_hash(exe) == EXPECTED_EXE, 'PLAS15_EXE_BUILD_MISMATCH')
    assert(runtime.module_hash(dll) == EXPECTED_DLL, 'PLAS15_DLL_BUILD_MISMATCH')

    local roots = discover.locate(runtime, reader, profile,
        { entity = true, projectile = true, explosion = true, damage = true })
    local catalog = catalog_module.capture(reader, roots.entity, profile,
        { 'WeaponDataComponentData', 'WeaponChargeComponentData' })
    local candidate = find_candidate(catalog, PLAS15)
    assert(candidate.entityRow == 3157, 'PLAS15_ENTITY_ROW_CHANGED')
    assert(candidate.ownership.WeaponDataComponentData.uniqueOwner,
        'PLAS15_WEAPON_DATA_NOT_UNIQUE')
    assert(candidate.ownership.WeaponChargeComponentData.uniqueOwner,
        'PLAS15_CHARGE_DATA_NOT_UNIQUE')

    local weapon = catalog.record(candidate, 'WeaponDataComponentData')
    local charge = catalog.record(candidate, 'WeaponChargeComponentData')
    local projectile = assert(roots.projectile.records[PLAS15_PROJECTILE], 'PLAS15_PROJECTILE_ROW_MISSING')
    local projectile_damage = assert(roots.damage.records[PLAS15_DAMAGE], 'PLAS15_DAMAGE_ROW_MISSING')
    local impact = assert(roots.explosion.records[PLAS15_IMPACT], 'PLAS15_IMPACT_ROW_MISSING')
    local impact_damage = assert(roots.damage.records[PLAS15_IMPACT_DAMAGE],
        'PLAS15_IMPACT_DAMAGE_ROW_MISSING')
    local overcharge_damage = assert(roots.damage.records[OVERCHARGE_DAMAGE],
        'PLAS15_OVERCHARGE_DAMAGE_ROW_MISSING')
    local overcharge = assert(roots.explosion.records[DEFAULT_OVERCHARGE],
        'PLAS15_OVERCHARGE_EXPLOSION_ROW_MISSING')

    assert(b.u32(charge.bytes, 4) == PLAS15_CHARGE_MEDIUM
        and b.u32(charge.bytes, 28) == PLAS15_CHARGE
        and b.u32(charge.bytes, 52) == PLAS15_CHARGE,
        'PLAS15_CHARGE_PROJECTILES_CHANGED')
    assert(same_number(b.value(charge.bytes, 0, 'f32'), 0.01)
        and same_number(b.value(charge.bytes, 24, 'f32'), 1)
        and same_number(b.value(charge.bytes, 48, 'f32'), 3),
        'PLAS15_CHARGE_TIMES_CHANGED')
    assert(b.u32(weapon.bytes, 144) == 5
        and (b.u32(weapon.bytes, 148) == 0 or b.u32(weapon.bytes, 148) == FIRE_MODE_SAFETY_OFF
            or b.u32(weapon.bytes, 148) == 6)
        and (b.u32(weapon.bytes, 184) == 0 or b.u32(weapon.bytes, 184) == FIREMODE_SELECTOR),
        'PLAS15_FIRE_MODE_LAYOUT_CHANGED')
    assert(b.u32(projectile.bytes, 60) == PLAS15_DAMAGE
        and b.u32(projectile.bytes, 144) == PLAS15_IMPACT,
        'PLAS15_PROJECTILE_LINK_CHANGED')
    assert(b.u32(impact.bytes, 4) == PLAS15_IMPACT_DAMAGE,
        'PLAS15_IMPACT_DAMAGE_LINK_CHANGED')

    local changes = {}
    add_change(changes, weapon, 148, 'u32', {0, 6, FIRE_MODE_SAFETY_OFF}, FIRE_MODE_SAFETY_OFF,
        'unsafe fire mode')
    add_change(changes, weapon, 184, 'u32', {0, FIREMODE_SELECTOR}, FIREMODE_SELECTOR,
        'weapon-wheel selector')
    add_change(changes, charge, 48, 'f32', 3, 4, 'overcharge warning threshold')
    add_change(changes, charge, 52, 'u32', PLAS15_CHARGE, PLAS15_PROJECTILE,
        'overcharge projectile')
    add_change(changes, charge, 132, 'u32', 0, EPOCH_WARNING, 'danger warning sound')
    add_change(changes, charge, 185, 'u8', 0, 1, 'overcharge explosion')
    add_change(changes, charge, 200, 'u32', b.u32(charge.bytes, 200), DEFAULT_OVERCHARGE,
        'overcharge explosion type')

    add_change(changes, projectile_damage, 4, 'i32', 100, 600, 'overcharge projectile damage')
    add_change(changes, projectile_damage, 12, 'u32', 2, 4, 'overcharge projectile AP direct')
    add_change(changes, projectile_damage, 16, 'u32', 2, 4, 'overcharge projectile AP slight')
    add_change(changes, projectile_damage, 20, 'u32', 2, 4, 'overcharge projectile AP large')
    add_change(changes, projectile_damage, 24, 'u32', 0, 4, 'overcharge projectile AP extreme')
    add_change(changes, impact_damage, 4, 'i32', 25, 400, 'overcharge impact damage')
    add_change(changes, impact_damage, 12, 'u32', 3, 4, 'overcharge impact AP direct')
    add_change(changes, impact_damage, 16, 'u32', 0, 4, 'overcharge impact AP slight')
    add_change(changes, impact_damage, 20, 'u32', 0, 4, 'overcharge impact AP large')
    add_change(changes, impact_damage, 24, 'u32', 0, 4, 'overcharge impact AP extreme')
    add_change(changes, overcharge, 16, 'f32', b.value(overcharge.bytes, 16, 'f32'), 0.5,
        'penalty inner radius')
    add_change(changes, overcharge, 20, 'f32', b.value(overcharge.bytes, 20, 'f32'), 4,
        'penalty outer radius')
    add_change(changes, overcharge_damage, 4, 'i32', b.value(overcharge_damage.bytes, 4, 'i32'), 1000,
        'penalty damage')
    add_change(changes, overcharge_damage, 8, 'i32', b.value(overcharge_damage.bytes, 8, 'i32'), 1000,
        'penalty durable damage')
    add_change(changes, overcharge_damage, 12, 'u32', b.u32(overcharge_damage.bytes, 12), 5,
        'penalty AP direct')
    add_change(changes, overcharge_damage, 16, 'u32', b.u32(overcharge_damage.bytes, 16), 5,
        'penalty AP slight')
    add_change(changes, overcharge_damage, 20, 'u32', b.u32(overcharge_damage.bytes, 20), 5,
        'penalty AP large')
    add_change(changes, overcharge_damage, 24, 'u32', b.u32(overcharge_damage.bytes, 24), 5,
        'penalty AP extreme')
    add_change(changes, overcharge_damage, 28, 'u32', b.u32(overcharge_damage.bytes, 28), 30,
        'penalty demolition')
    apply_changes(runtime, reader, changes)
    mod:log('PLAS-15 unsafe-mode authoring applied; current-magazine clearing remains runtime-state dependent')
end

local patch = coroutine.create(function()
    local ok, reason = pcall(patch_native)
    if not ok then mod:log('PLAS-15 patch refused: ' .. tostring(reason)) end
end)

hd2.every(0.1, function(timer)
    if coroutine.status(patch) == 'dead' then timer:cancel(); return end
    local ok, reason = coroutine.resume(patch)
    if not ok then timer:cancel(); mod:log('PLAS-15 patch coroutine failed: ' .. tostring(reason)) end
end)
