# class InfoRouter:
#     route_app_labels = {"info"}

#     def db_for_read(self, model, **hints):
#         """
#         Attempts to read info model goes to info_db.
#         """
#         if model._meta.app_label in self.route_app_labels:
#             return "info_db"
#         return None

#     def db_for_write(self, model, **hints):
#         """
#         Attempts to write info models go to info_db.
#         """
#         if model._meta.app_label in self.route_app_labels:
#             return "info_db"
#         return None

#     def allow_relation(self, obj1, obj2, **hints):
#         """
#         Allow relations if a model in the auth or contenttypes apps is
#         involved.
#         """
#         if (
#             obj1._meta.app_label in self.route_app_labels
#             or obj2._meta.app_label in self.route_app_labels
#         ):
#             return True
#         return None

#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         """
#         Make sure the info app only appear in the
#         'info_db' database.
#         """
#         if app_label in self.route_app_labels:
#             return db == "info_db"
#         return None
