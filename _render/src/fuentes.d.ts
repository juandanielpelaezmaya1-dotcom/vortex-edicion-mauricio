// Las fuentes .ttf se importan como URL (el bundler de Remotion las sirve como asset).
declare module "*.ttf" {
  const src: string;
  export default src;
}
