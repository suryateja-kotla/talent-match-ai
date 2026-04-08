import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  username = '';
  password = '';
  message = '';
  loading = false;
  showPassword = false;
  rememberMe = false;

  constructor(
    private auth: AuthService,
    private router: Router,
  ) {}

  login() {
    this.message = '';
    if (!this.username || !this.password) {
      this.message = 'Please enter username and password';
      return;
    }

    this.loading = true;

    // simulate network delay
    setTimeout(() => {
      const res = this.auth.login(this.username, this.password);

      this.loading = false;
      if (res.success && res.user) {
        if (this.rememberMe) {
          localStorage.setItem('currentUser', JSON.stringify(res.user));
        } else {
          sessionStorage.setItem('currentUser', JSON.stringify(res.user));
        }

        if (res.user.role === 'hr') {
          this.router.navigate(['/hr']);
        } else {
          this.router.navigate(['/user']);
        }
      } else {
        this.message = 'Invalid username or password';
      }
    }, 600);
  }
}
