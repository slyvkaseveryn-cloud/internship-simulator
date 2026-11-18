import { Link } from 'react-router-dom'
import { useAuth } from '../useAuth'

export default function Home() {
  const { signedIn } = useAuth()
  return (
    <section className="hero">
      <h1>Тестові завдання, як на відборі в IT</h1>
      <p className="lead">
        Отримуєш лист від менеджера, сирі дані й дедлайн — як у справжньому тестовому для junior.
        Здаєш роботу й отримуєш рев'ю як від тімліда: що добре, що виправити, що робити далі.
      </p>
      <p>Аналітика, бізнес-аналіз і QA. Кейс займає 2–4 години, а результат іде в портфоліо.</p>
      {signedIn ? (
        <Link to="/cases" className="btn">До кейсів</Link>
      ) : (
        <div className="actions">
          <Link to="/signup" className="btn">Зареєструватись</Link>
          <Link to="/signin" className="btn ghost">Увійти</Link>
        </div>
      )}
    </section>
  )
}
