elanor:
    type: assignment

    actions:
        on assignment:
            - trigger name:click state:true
            - trigger name:death state:true
            - follow followers:<npc> target:<player> lead:4 speed:1.0
            - run elanor_look
        on click:
            - chat "Coucou !"

        on death:
            - narrate "<red>Elanor : Capitaine... je suis désolée..." targets:<server.online_players>

elanor_look:
    type: task
    debug: false
    script:
        - while <npc.is_spawned>:
            - if <player.is_online>:
                - look <npc> <player.eye_location>
            - wait 5t

elanor_monde:
    type: world
    events:

        on script reload:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "recharger!"

        # 🌅 Lever du jour
        on time 6:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "C'est le matin!"

        # ☀️ Midi
        on time 12:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "C'est midi !"

        # 🌇 Coucher du soleil
        on time 18:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "C'est le soir !"
        # 🌙 Minuit
        on time 0:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "C'est minuit !"

        # 🌧️ La pluie commence
        on weather rains:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "C'est mouiller!"

        # ☀️ La pluie s'arrête
        on weather clears:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "C'est clair !"

        # ⛈️ Orage
        on thunder begins:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "tonere !"

        # 🌤️ Fin de l'orage
        on thunder clears:
            - define elanor <server.npcs_named[Elanor].first>
            - chat targets:<server.online_players> talkers:<[elanor]> "fini tonere !"