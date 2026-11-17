# Voz GUIA (no final): una frase por linea de guion.txt -> voz-off/guia-NN.wav con la voz OneCore instalada.
param([string]$Voz = "Laura", [string]$Ritmo = "-12%", [string]$Prefijo = "guia")
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Esperar($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(); $task.Result }
$s = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$s.Voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.DisplayName -like "*$Voz*" } | Select-Object -First 1
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$i = 0
foreach ($linea in Get-Content -Encoding UTF8 (Join-Path $dir "guion.txt")) {
  if (-not $linea.Trim()) { continue }
  $i++
  $ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='es-ES'><prosody rate='$Ritmo' pitch='-4%'>$linea</prosody></speak>"
  $st = Esperar ($s.SynthesizeSsmlToStreamAsync($ssml)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
  $r = New-Object Windows.Storage.Streams.DataReader($st.GetInputStreamAt(0))
  $n = [uint32]$st.Size
  $null = Esperar ($r.LoadAsync($n)) ([uint32])
  $b = New-Object byte[] $n; $r.ReadBytes($b)
  [IO.File]::WriteAllBytes((Join-Path $dir ("{0}-{1:D2}.wav" -f $Prefijo, $i)), $b)
  "{0}-{1:D2}.wav  {2}" -f $Prefijo, $i, $s.Voice.DisplayName
}
