import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { signOut } from './auth'
import { useAuth } from './useAuth'
import Home from './pages/Home'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Confirm from './pages/Confirm'
import ResetPassword from './pages/ResetPassword'
import Account from './pages/Account'

export default function App() {
  const { signedIn, claims } = useAuth()
  return (
    <>
      <header className="top">
        <Link to="/" className="logo">Симулятор стажувань</Link>
        <nav>
          {signedIn ? (
            <>
              <Link to="/account">{claims?.name || claims?.email || 'Кабінет'}</Link>
              <button className="link" onClick={signOut}>Вийти</button>
            </>
          ) : (
            <>
              <Link to="/signin">Увійти</Link>
              <Link to="/signup" className="btn small">Зареєструватись</Link>
            </>
          )}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/confirm" element={<Confirm />} />
          <Route path="/reset" element={<ResetPassword />} />
          <Route path="/account" element={signedIn ? <Account /> : <Navigate to="/signin" replace />} />
          <Route path="*" element={<p>Сторінку не знайдено. <Link to="/">На головну</Link></p>} />
        </Routes>
      </main>
    </>
  )
}
