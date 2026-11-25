Репозиторий пользователей
=========================

``UserRepository`` создаёт аккаунты, привязывает учётные данные и читает роли
из БД. При сохранении и поиске email используется его нормализованная форма.
Методы создания возвращают ``UserIdentity`` с внутренним ID и системным UUID.

.. automodule:: app.repositories.user_repository
   :members:
   :member-order: bysource
