import { Menu, LogIn, UserPlus, LogOut, User, LayoutDashboard } from 'lucide-react';
import { Button } from "@/components/ui/button.jsx";
import { Separator } from "@/components/ui/separator.jsx";
import { NavigationMenu, NavigationMenuList, NavigationMenuItem, NavigationMenuLink } from "@/components/ui/navigation-menu.jsx";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet.jsx";
import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext.jsx'
import { getDashboardPath } from '@/lib/auth.js'

function Navbar() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userName, setUserName] = useState('')
  const [userRole, setUserRole] = useState('')

  useEffect(() => {
    const userId = localStorage.getItem('userId')
    const name = localStorage.getItem('userName')
    const role = localStorage.getItem('userRole')
    if (userId && userId !== 'null' && userId !== 'undefined') {
      setIsLoggedIn(true)
      setUserName(name || 'User')
      setUserRole(role || '')
    }
  }, [])

  const dashboardPath = getDashboardPath(userRole)

  const handleLogout = () => {
    logout()
    setIsLoggedIn(false)
    navigate('/')
  }

  return (
    <header className="border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        <Link to="/">
          <div className="text-xl heading text-accent-gray cursor-pointer hover:opacity-80">SarvAwas AI</div>
        </Link>

        <div className="hidden md:flex items-center gap-6">
          {!isLoggedIn && (
            <>
              <NavigationMenu>
                <NavigationMenuList>
                  <NavigationMenuItem>
                    <NavigationMenuLink href="#journey">How It Works</NavigationMenuLink>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <NavigationMenuLink href="#ecosystem">Ecosystem</NavigationMenuLink>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <NavigationMenuLink href="#stories">Success Stories</NavigationMenuLink>
                  </NavigationMenuItem>
                  <NavigationMenuItem>
                    <NavigationMenuLink href="#invest">For Investors</NavigationMenuLink>
                  </NavigationMenuItem>
                </NavigationMenuList>
              </NavigationMenu>
              <Separator orientation="vertical" className="h-6" />
            </>
          )}
          
          {!isLoggedIn ? (
            <>
              <Link to="/login">
                <Button variant="outline" className="text-sm text-accent-gray border-accent-gray/20 hover:bg-gray-50">
                  <LogIn className="w-4 h-4 mr-2" />
                  Login
                </Button>
              </Link>
              <Link to="/sign-up">
                <Button className="text-sm bg-[#581C87] hover:bg-[#581C87]/90 text-white">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Register
                </Button>
              </Link>
            </>
          ) : (
            <>
              <span className="text-sm text-gray-700">Welcome, {userName}</span>
              <Link to={dashboardPath}>
                <Button variant="outline" className="text-sm text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-[#1E3A8A] hover:text-[#1E3A8A]">
                  <LayoutDashboard className="w-4 h-4 mr-2" />
                  Dashboard
                </Button>
              </Link>
              <Link to="/profile-settings">
                <Button variant="outline" className="text-sm text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-[#581C87] hover:text-[#581C87]">
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </Button>
              </Link>
              <Button 
                onClick={handleLogout}
                variant="outline" 
                className="text-sm text-red-600 border-red-200 hover:bg-red-50"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </>
          )}
        </div>

        <div className="md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open menu">
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <SheetHeader>
                <SheetTitle className="heading text-accent-gray">Menu</SheetTitle>
              </SheetHeader>
              {!isLoggedIn && (
                <>
                  <nav className="mt-6 grid gap-3">
                    <a href="#journey" className="text-sm text-gray-700 hover:text-accent-gray">How It Works</a>
                    <a href="#ecosystem" className="text-sm text-gray-700 hover:text-accent-gray">Ecosystem</a>
                    <a href="#stories" className="text-sm text-gray-700 hover:text-accent-gray">Success Stories</a>
                    <a href="#invest" className="text-sm text-gray-700 hover:text-accent-gray">For Investors</a>
                  </nav>
                  <Separator className="my-4" />
                </>
              )}
              <div className="grid gap-3">
                {!isLoggedIn ? (
                  <>
                    <Link to="/login">
                      <Button variant="outline" className="w-full text-accent-gray border-accent-gray/20 hover:bg-gray-50">
                        <LogIn className="w-4 h-4 mr-2" />
                        Login
                      </Button>
                    </Link>
                    <Link to="/sign-up">
                      <Button className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white">
                        <UserPlus className="w-4 h-4 mr-2" />
                        Register
                      </Button>
                    </Link>
                  </>
                ) : (
                  <>
                    <div className="text-sm text-gray-700 p-2">Welcome, {userName}</div>
                    <Link to={dashboardPath}>
                      <Button variant="outline" className="w-full text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-[#1E3A8A] hover:text-[#1E3A8A]">
                        <LayoutDashboard className="w-4 h-4 mr-2" />
                        Dashboard
                      </Button>
                    </Link>
                    <Link to="/profile-settings">
                      <Button variant="outline" className="w-full text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-[#581C87] hover:text-[#581C87]">
                        <User className="w-4 h-4 mr-2" />
                        Profile
                      </Button>
                    </Link>
                    <Button 
                      onClick={handleLogout}
                      className="w-full bg-red-600 hover:bg-red-700 text-white"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </Button>
                  </>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

export default Navbar;