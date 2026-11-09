# Estudio de edición de Vortex

El estudio con el que Vortex monta sus reels, con un equipo de cinco especialistas que
viven dentro de Claude Code. Mauricio le habla a Claude como a un editor asistente
(«edita este reel», «sube el texto del segundo 8») y Claude escribe el video, lo renderiza
y le muestra el borrador.

**Mauricio:** pégale a tu Claude el enlace de este repo y dile «instálalo». Lo que sigue es
para él.

## Instalación (para Claude)

Claude: instala el estudio en el equipo de Mauricio siguiendo estos pasos en orden. Háblale
de tú, en corto, y dile en qué paso vas.

1. **Clona el repo** en Documentos (Mac: `~/Documents`; Windows: `~/Documents` desde Git
   Bash), si no está clonado ya:
   `gh repo clone juandanielpelaezmaya1-dotcom/vortex-edicion-mauricio` o
   `git clone https://github.com/juandanielpelaezmaya1-dotcom/vortex-edicion-mauricio.git`.
   El repo es privado: si pide credenciales, que Mauricio corra `gh auth login` en una
   terminal (elige GitHub.com, HTTPS y autenticar git) con la cuenta a la que JD le dio
   acceso, y vuelve a intentar.

2. **Mira qué falta:** `node --version` (20.11 o más nuevo), `ffmpeg -version`,
   `git --version`, y Python (Mac: `python3 --version`; Windows: `py --version`).

3. **Instala solo lo que falte:**
   - Mac: si no hay Homebrew, pídele a Mauricio que pegue en la app Terminal
     `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
     (pide la clave del Mac, por eso lo corre él). Después `brew install node ffmpeg python`.
     Revisa también `xcode-select -p`: whisper se compila con esas herramientas; si faltan,
     `xcode-select --install`.
   - Windows: `winget install --accept-package-agreements --accept-source-agreements OpenJS.NodeJS.LTS Gyan.FFmpeg Python.Python.3.12`
   - Si después de instalar la terminal no encuentra un programa, es el PATH viejo: pídele a
     Mauricio que cierre y abra VS Code y te diga «sigue». No reinstales.

4. **El motor:** `cd _render && npm ci && cd ..`

5. **La prueba:** desde la raíz, `node herramientas/estudio.mjs test`. Tiene que terminar en
   `OK render` y `OK revision`. Saca un cuadro y míralo:
   `ffmpeg -y -ss 1.5 -i _prueba/cache/borrador.mp4 -frames:v 1 _prueba/cache/cuadro.jpg`.

6. **La hoja de revisión:**
   - Mac: `python3 -m venv .venv && .venv/bin/pip install pillow`
   - Windows: `py -m venv .venv && .venv/Scripts/pip install pillow`

7. **La RAM:** mírala (Mac: `sysctl -n hw.memsize`; Windows:
   `powershell -c "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"`) y ajusta
   `setConcurrency` en `_render/remotion.config.ts` según el comentario que tiene. Ese cambio
   es de este equipo: no lo subas.

8. **Cierra con Mauricio:** dile que quedó instalado y que abra la carpeta
   `vortex-edicion-mauricio` en VS Code y abra Claude **ahí, en una sesión nueva**: así se
   cargan el equipo de edición y las reglas (`CLAUDE.md`). La primera vez puede escribirle
   «Hola, soy Mauricio. Explícame cómo trabajamos un reel».

Si un paso falla y no sabes por qué, no improvises arreglos al estudio: dile a Mauricio qué
falló, con el error, para que se lo pase a JD.

## Cómo se trabaja un video

1. JD manda el guion y el material (por Drive).
2. A Claude: «Activa VEGA. Proyecto nuevo: `mvb-reel-la-mango`. El material está en
   Descargas/la-mango y el guion es este: …».
3. Claude arma el borrador y lo muestra. Se corrige hablando o dibujando sobre el cuadro
   («abre la revisión»).
4. El borrador va a JD. Cuando dice que sí: «exporta el final».
5. La carpeta `salida/` se sube a Drive y el proyecto se guarda en git («guarda y sube el
   proyecto»).

Antes de cada sesión, `git pull`, para tener las reglas y herramientas al día.
