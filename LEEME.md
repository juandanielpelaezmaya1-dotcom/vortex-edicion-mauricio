# Estudio de edición de Vortex

Hola, Mauricio. Este es tu estudio de edición: las herramientas con las que Vortex monta sus
reels y un equipo de cinco especialistas que viven dentro de tu Claude Code. Tú le hablas a
Claude como a un editor asistente («edita este reel», «sube el texto del segundo 8») y él
escribe el video, lo renderiza y te muestra el borrador.

La instalación toma unos 20 minutos y se hace una sola vez.

## 1. Instala lo necesario

### Mac

Abre la app **Terminal** y pega, una por una:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install node ffmpeg git python
curl -fsSL https://claude.ai/install.sh | bash
```

La primera instala Homebrew (te pide la clave del Mac) y las herramientas de línea de
comandos de Apple, que el estudio necesita para compilar el transcriptor de voz.

### Windows

Abre **PowerShell** y pega, una por una:

```
winget install OpenJS.NodeJS.LTS Gyan.FFmpeg Git.Git Python.Python.3.12
irm https://claude.ai/install.ps1 | iex
```

Cierra PowerShell y ábrelo de nuevo para que reconozca los programas nuevos.

### Los dos

- Instala **Visual Studio Code** (code.visualstudio.com) y, dentro de él, la extensión
  **Claude Code**.
- Necesitas una cuenta de Claude con plan Pro o Max.

## 2. Baja el estudio

En la terminal, desde la carpeta donde quieras tenerlo (por ejemplo, Documentos):

```
git clone <el enlace que te mandó JD>
cd vortex-edicion-mauricio/_render
npm ci
cd ..
node herramientas/estudio.mjs test
```

El último comando arma un video de prueba. Si termina con `OK render` y `OK revision`, el
estudio funciona. Si falla, abre Claude (paso 3) y pégale el error.

Para la hoja de revisión (un cuadro por frase, para revisar rápido):

- Mac: `python3 -m venv .venv && .venv/bin/pip install pillow`
- Windows: `py -m venv .venv` y después `.venv\Scripts\pip install pillow`

## 3. Empieza acá

1. Abre la carpeta `vortex-edicion-mauricio` en Visual Studio Code.
2. Abre Claude Code (el ícono de Claude en la barra, o escribe `claude` en la terminal de
   VS Code) e inicia sesión con tu cuenta.
3. Pega esto:

```
Hola, soy Mauricio. Revisa que el estudio esté bien instalado (corre el test), mira cuánta
RAM tiene mi equipo y ajusta la concurrencia del render. Después explícame en pocas líneas
cómo trabajamos un reel de principio a fin.
```

## Cómo se trabaja un video

1. JD te manda el guion y el material (por Drive).
2. Le dices a Claude: «Activa VEGA. Proyecto nuevo: `mvb-reel-la-mango`. El material está
   en Descargas/la-mango y el guion es este: …».
3. Claude arma el borrador y te lo muestra. Lo corriges hablando o dibujando sobre el cuadro
   («abre la revisión»).
4. Le mandas el borrador a JD. Cuando dice que sí, «exporta el final».
5. Subes la carpeta `salida/` a Drive y haces commit y push del proyecto («guarda y sube
   el proyecto»).

## Antes de cada sesión

```
git pull
```

Así tienes las reglas y herramientas al día.
