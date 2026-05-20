import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';

class CameraServiceFlet extends FletService {
  CameraServiceFlet({required super.control});

  final ImagePicker _picker = ImagePicker();

  @override
  void init() {
    super.init();
    debugPrint("CameraServiceFlet(${control.id}).init");
    control.addInvokeMethodListener(_invokeMethod);
  }

  @override
  void dispose() {
    debugPrint("CameraServiceFlet(${control.id}).dispose");
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    debugPrint("CameraService.$name($args)");
    switch (name) {
      case "pick_image_from_camera":
        try {
          final XFile? image = await _picker.pickImage(
            source: ImageSource.camera,
            imageQuality: 88,
            maxWidth: 1920,
            maxHeight: 1920,
          );
          debugPrint("CameraService.pick_image_from_camera result: ${image?.path}");
          return image?.path;
        } catch (e, st) {
          debugPrint("CameraService ERROR (camera): $e\n$st");
          return "ERROR:$e";
        }
      case "pick_image_from_gallery":
        try {
          final XFile? image = await _picker.pickImage(
            source: ImageSource.gallery,
            imageQuality: 88,
            maxWidth: 1920,
            maxHeight: 1920,
          );
          debugPrint("CameraService.pick_image_from_gallery result: ${image?.path}");
          return image?.path;
        } catch (e, st) {
          debugPrint("CameraService ERROR (gallery): $e\n$st");
          return "ERROR:$e";
        }
      default:
        throw Exception("Unknown CameraService method: $name");
    }
  }
}
