import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:audioplayers/audioplayers.dart' as ap;

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

  /// Percorre a árvore de widgets a partir da raiz para encontrar um Navigator.
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
        return result;
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

class _BarcodeScannerPageState extends State<_BarcodeScannerPage>
    with SingleTickerProviderStateMixin {
  late final MobileScannerController _controller;
  late final AnimationController _scanAnim;
  late final ap.AudioPlayer _audioPlayer;
  bool _detected = false;
  bool _flashGreen = false;

  static const double _mirW = 280;
  static const double _mirH = 180;

  @override
  void initState() {
    super.initState();
    _controller = MobileScannerController(
      detectionSpeed: DetectionSpeed.normal,
      facing: CameraFacing.back,
      torchEnabled: false,
    );
    // Linha de varredura oscila de cima a baixo continuamente
    _scanAnim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);

    _audioPlayer = ap.AudioPlayer();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scanAnim.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_detected) return;
    final barcodes = capture.barcodes;
    if (barcodes.isEmpty) return;
    final rawValue = barcodes.first.rawValue;
    if (rawValue == null || rawValue.isEmpty) return;
    _detected = true;

    // Beep sonoro (beep.mp3 em assets/) + vibração tátil
    try {
      HapticFeedback.mediumImpact();
      await _audioPlayer.play(ap.AssetSource('beep.mp3'));
    } catch (_) {}

    // Flash verde na mira por 350 ms antes de fechar
    if (mounted) setState(() => _flashGreen = true);
    await Future.delayed(const Duration(milliseconds: 350));

    if (mounted) Navigator.of(context).pop(rawValue);
  }

  @override
  Widget build(BuildContext context) {
    final Color mirColor = _flashGreen ? Colors.greenAccent : Colors.white;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text(
          'Escanear Código',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
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
          // Câmera ao vivo
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),

          // Overlay escuro fora da mira
          ColorFiltered(
            colorFilter: ColorFilter.mode(
              Colors.black.withOpacity(0.55),
              BlendMode.srcOut,
            ),
            child: Stack(
              children: [
                Container(decoration: const BoxDecoration(color: Colors.black, backgroundBlendMode: BlendMode.dstOut)),
                Center(
                  child: Container(
                    width: _mirW,
                    height: _mirH,
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Cantos da mira + linha de varredura animada
          Center(
            child: SizedBox(
              width: _mirW,
              height: _mirH,
              child: Stack(
                children: [
                  // Cantos estilizados (CustomPainter)
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _CornersPainter(color: mirColor),
                    ),
                  ),
                  // Linha de varredura
                  AnimatedBuilder(
                    animation: _scanAnim,
                    builder: (_, __) {
                      final topOffset = 8 + _scanAnim.value * (_mirH - 16);
                      return Positioned(
                        top: topOffset,
                        left: 12,
                        right: 12,
                        child: Container(
                          height: 2,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                Colors.transparent,
                                mirColor.withOpacity(0.9),
                                mirColor,
                                mirColor.withOpacity(0.9),
                                Colors.transparent,
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),

          // Instrução na base
          Positioned(
            bottom: 44,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.65),
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

// ─── Pintor dos cantos da mira ────────────────────────────────────────────────

class _CornersPainter extends CustomPainter {
  final Color color;
  const _CornersPainter({required this.color});

  static const double _arm = 26.0;   // comprimento do braço do canto
  static const double _thick = 3.5;  // espessura da linha

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = _thick
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final w = size.width;
    final h = size.height;

    // Canto superior esquerdo
    canvas.drawLine(const Offset(0, _arm), const Offset(0, 0), paint);
    canvas.drawLine(const Offset(0, 0), const Offset(_arm, 0), paint);

    // Canto superior direito
    canvas.drawLine(Offset(w - _arm, 0), Offset(w, 0), paint);
    canvas.drawLine(Offset(w, 0), Offset(w, _arm), paint);

    // Canto inferior esquerdo
    canvas.drawLine(Offset(0, h - _arm), Offset(0, h), paint);
    canvas.drawLine(Offset(0, h), Offset(_arm, h), paint);

    // Canto inferior direito
    canvas.drawLine(Offset(w - _arm, h), Offset(w, h), paint);
    canvas.drawLine(Offset(w, h), Offset(w, h - _arm), paint);
  }

  @override
  bool shouldRepaint(_CornersPainter old) => old.color != color;
}
