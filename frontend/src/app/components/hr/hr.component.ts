import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-hr',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hr.component.html',
  styleUrl: './hr.component.scss'
})
export class HrComponent {

  constructor(private auth: AuthService) {}
  jobs = [
    {
      title: 'Senior Frontend Developer',
      skills: ['React', 'TypeScript', 'Next.js'],
      exp: '5+ yrs',
      location: 'San Francisco',
      positions: 2,
      applicants: 12
    },
    {
      title: 'Full Stack Engineer',
      skills: ['Node.js', 'React', 'Docker'],
      exp: '3+ yrs',
      location: 'Remote',
      positions: 3,
      applicants: 24
    },
    {
      title: 'UX Designer',
      skills: ['Figma', 'Research', 'Prototyping'],
      exp: '4+ yrs',
      location: 'New York',
      positions: 1,
      applicants: 8
    }
  ];
  logout() {
    this.auth.logout();
  }
}