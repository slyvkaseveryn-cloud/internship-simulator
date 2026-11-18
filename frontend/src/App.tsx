import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { signOut } from './auth'
import { useAuth } from './useAuth'
import RequireAuth from './RequireAuth'
import Home from './pages/Home'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Confirm from './pages/Confirm'
import ResetPassword from './pages/ResetPassword'
import Roles from './pages/Roles'
import RoleCases from './pages/RoleCases'
import CasePage from './pages/CasePage'

const guard = (el: React.ReactNode) => <RequireAuth>{el}</RequireAuth>

export default function App() {
  const { signedIn } = useAuth()
  return (
    <>
      <header className="top">
        <Link to="/" className="logo">Симулятор стажувань</Link>
        <nav>
          {signedIn ? (
            <>
              <Link to="/cases">Кейси</Link>
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
          <Route path="/cases" element={guard(<Roles />)} />
          <Route path="/roles/:role" element={guard(<RoleCases />)} />
          <Route path="/cases/:id" element={guard(<CasePage />)} />
          <Route path="/account" element={<Navigate to="/cases" replace />} />
          <Route path="*" element={<p>Сторінку не знайдено. <Link to="/">На головну</Link></p>} />
        </Routes>
      </main>
    </>
  )
}
