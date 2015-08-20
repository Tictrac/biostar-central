from django_auth_ldap.backend import LDAPBackend


class TictracLDAPBackend(LDAPBackend):
    def get_or_create_user(self, username, ldap_user):
        model = self.get_user_model()
        email = ldap_user.attrs.get('mail')
        if email:
            username_field = getattr(model, 'USERNAME_FIELD', 'username')

            kwargs = {
                'email__iexact': email[0],
                'defaults': {username_field: username.lower()}
            }
            user, new = model.objects.get_or_create(**kwargs)
        else:
            user, new = super(TictracLDAPBackend, self).get_or_create_user(username, ldap_user)
        user.name = ldap_user.attrs.get('displayname')[0]
        user.save()
        return user, new
