# Among Us (Pygame)

Clon de **Among Us** para un jugador, escrito en Python con Pygame. Juegas contra 7 bots en una nave con 13 habitaciones, ventilas, tareas con minijuegos y reuniones con votación.

## Cómo ejecutarlo en Visual Studio Code

1. Instala [Python 3.8+](https://www.python.org/downloads/) y la extensión **Python** de VS Code.
2. Abre esta carpeta en VS Code (`Archivo > Abrir carpeta...`).
3. Abre la terminal (`Ctrl + ñ` o `Ver > Terminal`) e instala Pygame:
   ```bash
   python -m pip install -r requirements.txt
   ```
   (En macOS/Linux puede ser `python3` en lugar de `python`.)
4. Ejecuta el juego de cualquiera de estas formas:
   - Pulsa **F5** (usa la configuración "Jugar Among Us").
   - Pulsa **Ctrl + Shift + B** (tarea de compilación por defecto).
   - O en la terminal: `python amongus.py`.

## Controles

| Tecla | Acción |
|---|---|
| WASD / Flechas | Moverse |
| E | Usar: hacer tarea / botón de emergencia (en la Cafetería) |
| R | Reportar un cadáver cercano |
| Q | Matar (solo impostor) |
| V | Entrar en una ventila y saltar a la siguiente (solo impostor) |
| M / TAB | Mapa |
| Ratón | Minijuegos y votaciones |
| ESC | Salir de una tarea / volver al menú |

En el menú: **1** o **ENTER** rol aleatorio, **2** tripulante, **3** impostor.

## Reglas

- **Tripulante**: completa tus tareas (marcadas con `!` amarillo y en el mapa). La tripulación gana si se completan todas las tareas o si se expulsa a todos los impostores. Si te matan, sigues como fantasma y puedes terminar tus tareas.
- **Impostor**: mata tripulantes (tiempo de recarga de 25 s) y usa las ventilas. Ganas cuando los impostores igualan en número a los tripulantes. ¡Cuidado! Los bots que te vean matar o usar una ventila te acusarán en la reunión.
- **Reuniones**: se abren al reportar un cadáver o al pulsar el botón de emergencia (una vez por partida). Lee el chat de los bots, haz clic en un jugador para votar o salta el voto. El más votado es expulsado.

## Minijuegos

- **Arreglar cables**: une cada cable con su color.
- **Descargar datos**: pulsa el botón y espera a que termine la barra.
- **Desbloquear colectores**: pulsa los números del 1 al 10 en orden.
- **Calibrar distribuidor**: pulsa ESPACIO cuando el indicador esté en la zona verde.

Puedes cambiar el número de jugadores, impostores, tareas o tiempos en las constantes del principio de `amongus.py`.
