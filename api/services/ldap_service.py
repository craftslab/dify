import logging

from ldap3 import ALL, AUTO_BIND_NO_TLS, SUBTREE, Connection, Server

from configs import dify_config
from extensions.ext_database import db
from models.account import Account, AccountStatus


class LdapService:
    def __init__(self):
        self.logger = logging.getLogger('ldap_service')

    def authenticate(self, username, password):
        """
        Authenticate user against LDAP server
        """
        if not dify_config.LDAP_ENABLED:
            return None

        try:
            # Connect to LDAP server
            server = Server(dify_config.LDAP_SERVER_URI, get_info=ALL)

            # Construct user DN
            user_dn = dify_config.LDAP_USER_DN_TEMPLATE.format(username=username)

            # Attempt to bind with user credentials
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=AUTO_BIND_NO_TLS
            )

            if not conn.bound:
                return None

            # Search for user details if needed
            if dify_config.LDAP_SEARCH_BASE:
                conn.search(
                    search_base=dify_config.LDAP_SEARCH_BASE,
                    search_filter=dify_config.LDAP_SEARCH_FILTER.format(username=username),
                    search_scope=SUBTREE,
                    attributes=dify_config.LDAP_ATTRIBUTES.split(",")
                )

                if not conn.entries or len(conn.entries) == 0:
                    return None

                user_data = conn.entries[0]
                email = getattr(user_data, 'mail', None)
                name = getattr(user_data, 'cn', None)
            else:
                # If no search is configured, use username as email
                email = username
                name = username

            # Provision or get the user
            return self._get_or_create_user(username, email, name)

        except Exception as e:
            self.logging.exception("LDAP authentication error")
            return None

    def _get_user(self, username, email, name):
        """
        Get existing user based on LDAP authentication
        """
        # Check if user exists by username
        account = Account.query.filter_by(username=username).first()

        if not account and email:
            # If not found by username, try by email
            account = Account.query.filter_by(email=email).first()

        if account:
            # Update existing user if needed
            if account.status != AccountStatus.ACTIVE:
                account.status = AccountStatus.ACTIVE
                db.session.commit()
            return account

        # Create new user if auto-provision is enabled
        if dify_config.LDAP_AUTO_PROVISION:
            try:
                account = Account(
                    username=username,
                    email=email or f"{username}@{dify_config.LDAP_DEFAULT_EMAIL_DOMAIN}",
                    name=name or username,
                    status=AccountStatus.ACTIVE,
                    interface_language='en-US',
                    timezone='UTC'
                )
                db.session.add(account)
                db.session.commit()
                return account
            except Exception as e:
                self.logging.exception("Failed to create LDAP user")
                db.session.rollback()
                return None

        return None
