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
    { username: 'user3', password: 'pass3', role: 'user' },
  ];

  constructor(private router: Router) {}

  login(username: string, password: string): { success: boolean; user?: Partial<User> } {
    if (username === this.hr.username) {
      if (password === this.hr.password) {
        const user = { username: this.hr.username, role: this.hr.role };
        localStorage.setItem('currentUser', JSON.stringify(user));
        return { success: true, user };
      }
      return { success: false };
    }

    const found = this.users.find(u => u.username === username && u.password === password);
    if (found) {
      const user = { username: found.username, role: found.role };
      localStorage.setItem('currentUser', JSON.stringify(user));
      return { success: true, user };
    }
    return { success: false };
  }

  getCurrentUser(): { username: string; role: string } | null {
    const raw = localStorage.getItem('currentUser')|| sessionStorage.getItem('currentUser');
    return raw ? JSON.parse(raw) : null;
  }

  getUserList(): { username: string }[] {
    return this.users.map(u => ({ username: u.username }));
  }

  getHrUsername(): string {
    return this.hr.username;
  }

  logout(): void {
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('currentUser');
    localStorage.removeItem('chat_session_id'); // ← clear session on logout too
    this.router.navigate(['/']);
  }
}