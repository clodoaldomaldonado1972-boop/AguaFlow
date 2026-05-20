import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';
import 'camera_service.dart';

class CameraExtension extends FletExtension {
  @override
  FletService? createService(Control control) {
    if (control.type == "CameraService") {
      return CameraServiceFlet(control: control);
    }
    return null;
  }

  @override
  Widget? createWidget(Key? key, Control control) {
    return null;
  }
}
