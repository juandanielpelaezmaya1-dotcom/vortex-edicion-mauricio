import { Config } from "@remotion/cli/config";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
// Cada cuadro se captura como JPEG antes de codificar: al 80 (el defecto) ablandaba la
// imagen en todos los cuadros. A 95 no se distingue del PNG y sigue siendo rapido.
Config.setJpegQuality(95);
Config.setCrf(16);
// Rango de TV (bt709): sin esto sale yuvj420p (rango completo) y cada reproductor lo
// interpreta a su manera: contraste y negros cambian entre el Mac, el iPhone e Instagram.
Config.setColorSpace("bt709");
Config.setOverwriteOutput(true);
Config.setCodec("h264");

// Concurrencia = cuantos Chrome abre Remotion a la vez para renderizar cuadros. Con 8 GB
// de RAM, 2 (mas se queda sin memoria y el render muere con "Timeout exceeded rendering
// the component"). Con 16 GB o mas, sube a 4; con 32 GB, a 6: el render va casi al doble.
Config.setConcurrency(2);
