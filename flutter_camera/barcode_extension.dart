import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';
import 'barcode_service.dart';

class BarcodeScannerExtension extends FletExtension {
  @override
  FletService? createService(Control control) {
    if (control.type == "BarcodeScannerService") {
      return BarcodeScannerServiceFlet(control: control);
    }
    return null;
  }

  @override
  Widget? createWidget(Key? key, Control control) {
    return null;
  }
}
