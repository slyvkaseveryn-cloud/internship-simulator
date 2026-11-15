import { Link } from 'react-router-dom'
import { useAuth } from '../useAuth'

export default function Home() {
  const { signedIn } = useAuth()
  return (
    <section className="hero">
      <h1>Тестові завдання, як на відборі в IT-компанію</h1>
      <p className="lead">
        Розмитий лист від менеджера, сирі дані, дедлайн і рев'ю як від тімліда.
        На виході — робота для портфоліо.
      </p>
      <p>Аналітика, бізнес-аналіз і QA. Кейс займає 2–4 години.</p>
      {signedIn ? (
        <Link to="/account" className="btn">Перейти до кабінету</Link>
      ) : (
        <div className="actions">
          <Link to="/signup" className="btn">Зареєструватись</Link>
          <Link to="/signin" className="btn ghost">Увійти</Link>
        </div>
      )}
    </section>
  )
}
