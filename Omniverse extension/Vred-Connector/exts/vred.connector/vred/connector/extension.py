import omni.ext
import carb

from omni.services.core import main
from .services import router


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class VredConnectorExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        ext_name = ext_id.split("-")[0]
        carb.log_info("[vred.connector] vred connector startup")

        # At this point, we register our Service's `router` under the prefix we gave our API using the settings system,
        # to facilitate its configuration and to ensure it is unique from all other extensions we may have enabled:
        url_prefix = carb.settings.get_settings().get_as_string(f"exts/{ext_name}/url_prefix")
        main.register_router(router=router, prefix=url_prefix, tags=["Vred Connector"],)

    def on_shutdown(self):
        carb.log_info("[vred.connector] vred connector shutdown")

        # When disabling the extension or shutting down the instance of the Omniverse application, let's make sure we
        # also deregister our Service's `router` in order to avoid our API being erroneously advertised as present as
        # part of the OpenAPI specification despite our handler function no longer being available:
        main.deregister_router(router=router)
