import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-neutral-800 mt-auto">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-6 text-sm text-neutral-500">
          <Link to="/about" className="hover:text-neutral-300 transition-colors">
            {t('footer.about')}
          </Link>
          <Link to="/terms" className="hover:text-neutral-300 transition-colors">
            {t('footer.terms')}
          </Link>
          <Link to="/privacy" className="hover:text-neutral-300 transition-colors">
            {t('footer.privacy')}
          </Link>
          <Link to="/faq" className="hover:text-neutral-300 transition-colors">
            {t('footer.faq')}
          </Link>
          <a href="mailto:support@sweetsin.cc" className="hover:text-neutral-300 transition-colors">
            {t('footer.contact')}
          </a>
        </div>
        <p className="text-center text-xs text-neutral-600 mt-3">
          {t('footer.copyright', { year })}
        </p>
      </div>
    </footer>
  );
}
