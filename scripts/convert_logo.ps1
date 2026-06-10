# Requires ImageMagick (magick) installed and in PATH
param(
  [string]$svgPath = "assets/logo.svg",
  [string]$outDir = "assets/icons"
)

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# Generate PNGs
magick convert -background none $svgPath -resize 256x256 $outDir\logo-256.png
magick convert -background none $svgPath -resize 64x64 $outDir\logo-64.png
magick convert -background none $svgPath -resize 32x32 $outDir\logo-32.png
magick convert -background none $svgPath -resize 16x16 $outDir\logo-16.png

# Generate .ico (Windows shortcut / installer)
magick convert $outDir\logo-16.png $outDir\logo-32.png $outDir\logo-64.png $outDir\logo-256.png $outDir\logo.ico

Write-Host "Generated icons in" $outDir
