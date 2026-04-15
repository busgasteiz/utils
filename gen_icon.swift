import AppKit

let canvasSize = CGSize(width: 1024, height: 1024)
let accentColor = NSColor(red: 0x60/255.0, green: 0xA5/255.0, blue: 0x89/255.0, alpha: 1.0)

func makeIcon(outputPath: String) {
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(canvasSize.width),
        pixelsHigh: Int(canvasSize.height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .calibratedRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    )!

    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = ctx

    // Background
    accentColor.setFill()
    NSBezierPath(rect: NSRect(origin: .zero, size: canvasSize)).fill()

    // SF Symbol bus.fill in white, centered
    let symbolSize: CGFloat = 620
    let config = NSImage.SymbolConfiguration(pointSize: symbolSize, weight: .regular)
    guard let busSymbol = NSImage(systemSymbolName: "bus.fill", accessibilityDescription: nil),
          let configured = busSymbol.withSymbolConfiguration(config) else {
        print("ERROR: could not load bus.fill symbol")
        exit(1)
    }

    // Tint white by drawing with NSColor.white
    let tinted = NSImage(size: configured.size)
    tinted.lockFocus()
    NSColor.white.set()
    configured.draw(at: .zero, from: .zero, operation: .sourceOver, fraction: 1.0)
    let colorRect = NSRect(origin: .zero, size: configured.size)
    NSColor.white.setFill()
    colorRect.fill(using: .sourceAtop)
    tinted.unlockFocus()

    let iconSize = tinted.size
    let x = (canvasSize.width - iconSize.width) / 2
    let y = (canvasSize.height - iconSize.height) / 2
    tinted.draw(in: NSRect(x: x, y: y, width: iconSize.width, height: iconSize.height))

    NSGraphicsContext.restoreGraphicsState()

    let pngData = rep.representation(using: .png, properties: [:])!
    try! pngData.write(to: URL(fileURLWithPath: outputPath))
    print("Saved: \(outputPath)")
}

makeIcon(outputPath: "/tmp/AppIcon-1024.png")
