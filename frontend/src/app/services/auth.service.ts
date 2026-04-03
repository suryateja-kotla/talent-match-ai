import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
interface User {
  username: string;
  password: string;
  role: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private hr: User = { username: 'hr', password: 'hrpass', role: 'hr' };
  private users: User[] = [
    { username: 'user1', password: 'pass1', role: 'user' },
    { username: 'user2', password: 'pass2', role: 'user' },
    { username: 'user3', password: 'pass3', role: 'user' }
  ];

  constructor(private router: Router) {}

  login(username: string, password: string): { success: boolean; user?: Partial<User> } {
    // If username matches HR, validate HR credentials
    if (username === this.hr.username) {
      if (password === this.hr.password) {
        return { success: true, user: { username: this.hr.username, role: this.hr.role } };
      }
      return { success: false };
    }

    // Otherwise check normal users
    const found = this.users.find(u => u.username === username && u.password === password);
    if (found) return { success: true, user: { username: found.username, role: found.role } };
    return { success: false };
  }

  getUserList(): { username: string }[] {
    return this.users.map(u => ({ username: u.username }));
  }

  getHrUsername(): string {
    return this.hr.username;
  }
  logout() {
    localStorage.removeItem('currentUser');
    this.router.navigate(['/']);
  }
}
