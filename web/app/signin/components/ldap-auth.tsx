import { useTranslation } from 'react-i18next'

type LdapAuthProps = {
  disabled?: boolean
}

export default function LdapAuth(props: LdapAuthProps) {
  const { t } = useTranslation()

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div className="mb-5">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            {t('login.emailOrUsername')}
          </label>
          <input
            type="text"
            name="email"
            id="email"
            placeholder={t('login.emailOrUsernamePlaceholder')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
        </div>
      </form>
    </div>
  )
}
