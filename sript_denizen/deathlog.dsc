death_logger2:
    type: world
    events:
        on player dies:
            - define lieu <player.location.xyz>
            - define monde <player.world.name>
            - define nom <player.name>
            - narrate "<&c>[MORT]<&r> <def[nom]> est morte dans <def[monde]> aux coordonnées <def[lieu]>" targets:<server.online_players>
            - ~log "[MORT] <def[nom]> — monde: <def[monde]> — lieu: <def[lieu]>" type:none file:deaths.log