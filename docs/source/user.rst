API пользователей
=================

Все маршруты принимают запросы ``POST``:

* ``/api/v1/users/id`` создаёт аккаунт с новым системным ID.
* ``/api/v1/users`` создаёт аккаунт по email и паролю. Если передан ``system_id``, привязывает их к существующему аккаунту.
* ``/api/v1/sessions`` выполняет вход по email и паролю.
* ``/api/v1/sessions/id`` выполняет вход по системному ID.
* ``/api/v1/tokens/refresh`` обменивает refresh-токен на новую пару токенов.

Эндпоинты
---------

.. automodule:: app.features.user.route
   :members: signup_with_id, signup_classic, login_classic, login_with_id, get_refresh_token
   :member-order: bysource

Схемы запросов и ответов
------------------------

.. automodule:: app.features.user.schemas
   :members:
   :member-order: bysource
