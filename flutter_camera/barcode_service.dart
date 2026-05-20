import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class BarcodeScannerServiceFlet extends FletService {
  BarcodeScannerServiceFlet({required super.control});

  @override
  void init() {
    super.init();
    debugPrint("BarcodeScannerServiceFlet(${control.id}).init");
    control.addInvokeMethodListener(_invokeMethod);
  }

  @override
  void dispose() {
    debugPrint("BarcodeScannerServiceFlet(${control.id}).dispose");
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }

  /// Percorre a árvore de widgets a partir da raiz para encontrar um
  /// elemento Navigator. Necessário porque rootElement está ACIMA do
  /// MaterialApp — usar rootElement diretamente em Navigator.of() causa
  /// "Null check operator used on a null value".
  BuildContext? _findNavigatorContext() {
    BuildContext? found;
    void visitor(Element element) {
      if (found != null) return;
      if (element.widget is Navigator) {
        found = element;
      } else {
        element.visitChildren(visitor);
      }
    }
    WidgetsBinding.instance.rootElement?.visitChildren(visitor);
    return found;
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    debugPrint("BarcodeService.$name($args)");
    if (name == "scan_barcode") {
      try {
        final BuildContext? ctx = _findNavigatorContext();
        if (ctx == null) return "ERROR:Navigator nao encontrado na arvore";

        final String? result = await Navigator.of(ctx).push<String>(
          MaterialPageRoute(
            fullscreenDialog: true,
            builder: (_) => const _BarcodeScannerPage(),
          ),
        );
        debugPrint("BarcodeService.scan_barcode result: $result");
        return result; // null = cancelado
      } catch (e, st) {
        debugPrint("BarcodeService ERROR: $e\n$st");
        return "ERROR:$e";
      }
    }
    return null;
  }
}

// ─── Tela de scanner em tempo real ───────────────────────────────────────────

class _BarcodeScannerPage extends StatefulWidget {
  const _BarcodeScannerPage();

  @override
  State<_BarcodeScannerPage> createState() => _BarcodeScannerPageState();
}

class _BarcodeScannerPageState extends State<_BarcodeScannerPage> {
  late final MobileScannerController _controller;
  bool _detected = false;

  @override
  void initState() {
    super.initState();
    _controller = MobileScannerController(
      detectionSpeed: DetectionSpeed.normal,
      facing: CameraFacing.back,
      torchEnabled: false,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_detected) return;
    final barcodes = capture.barcodes;
    if (barcodes.isEmpty) return;
    final rawValue = barcodes.first.rawValue;
    if (rawValue == null || rawValue.isEmpty) return;
    _detected = true;
    Navigator.of(context).pop(rawValue);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('Escanear Código', style: TextStyle(color: Colors.white, fontSize: 16)),
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(null),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            tooltip: 'Lanterna',
            onPressed: () => _controller.toggleTorch(),
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),
          // Mira de escaneamento
          Center(
            child: Container(
              width: 280,
              height: 180,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.red, width: 2.5),
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          // Instrução na base
          Positioned(
            bottom: 48,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'Aponte para o QR code ou código de barras do medidor',
                  style: TextStyle(color: Colors.white, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
