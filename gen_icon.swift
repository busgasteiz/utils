import AppKit
import Foundation

// Paths resolved relative to this script file
let scriptDir = URL(fileURLWithPath: #file).deletingLastPathComponent()
let repoRoot  = scriptDir.deletingLastPathComponent()

let accentColorURL = repoRoot
    .appendingPathComponent("ios/BusGasteiz/BusGasteiz/Assets.xcassets/AccentColor.colorset/Contents.json")
let appIconURL = repoRoot
    .appendingPathComponent("ios/BusGasteiz/BusGasteiz/Assets.xcassets/AppIcon.appiconset/AppIcon.png")

// Parse the AccentColor from its colorset Contents.json
func loadAccentColor(from url: URL) -> NSColor {
    guard let data = try? Data(contentsOf: url),
          let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let colors = json["colors"] as? [[String: Any]],
          // Prefer the universal idiom; fall back to the first entry
          let entry = colors.first(where: { ($0["idiom"] as? String) == "universal" }) ?? colors.first,
          let colorDict = entry["color"] as? [String: Any],
          let components = colorDict["components"] as? [String: String]
    else {
        print("ERROR: could not parse AccentColor from \(url.path)")
        exit(1)
    }

    func component(_ key: String) -> CGFloat {
        guard let raw = components[key] else { return 0 }
        if raw.hasPrefix("0x") || raw.hasPrefix("0X") {
            return CGFloat(Int(raw.dropFirst(2), radix: 16) ?? 0) / 255.0
        }
        return CGFloat(Double(raw) ?? 0)
    }

    let r = component("red")
    let g = component("green")
    let b = component("blue")
    let a = component("alpha")

    let space = colorDict["color-space"] as? String ?? "srgb"
    if space == "display-p3" {
        return NSColor(displayP3Red: r, green: g, blue: b, alpha: a)
    } else {
        return NSColor(srgbRed: r, green: g, blue: b, alpha: a)
    }
}

let canvasSize  = CGSize(width: 1024, height: 1024)
let accentColor = loadAccentColor(from: accentColorURL)
print("AccentColor: \(accentColor)")

func makeIcon(outputURL: URL) {
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
    try! pngData.write(to: outputURL)
    print("Saved: \(outputURL.path)")
}

makeIcon(outputURL: appIconURL)
