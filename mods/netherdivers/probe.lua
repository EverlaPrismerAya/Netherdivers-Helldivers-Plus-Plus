-- HD2-Addon: mods/netherdivers/probe
local loader = rawget(_G, "CowboyBingusModLoader")
if not loader then
    return
end
if (loader.api or 0) < 1 then
    return
end
_G.NetherdiversProbe = _G.NetherdiversProbe or { api = loader.api, version = loader.version }
