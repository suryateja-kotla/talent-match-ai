import { Component } from '@angular/core';
import { JobService } from '../../../services/job.service';
import { CommonModule } from '@angular/common';
import { Input } from '@angular/core';

@Component({
  selector: 'app-job-matches',
  standalone: true,
  imports: [],
  templateUrl: './job-matches.component.html',
  styleUrl: './job-matches.component.scss',
})
export class JobMatchesComponent {
  matchedJobs: any[] = [];
  isLoading = false;
  @Input() allJobPostings: any[] = [];

  constructor(private jobService: JobService) {}

  ngOnInit() {
    this.loadMatches();
  }

  loadMatches() {
    this.isLoading = true;
    this.jobService.getJobs().subscribe({
      next: (jobs) => {
        this.matchedJobs = jobs;
        this.isLoading = false;
      },
      error: () => (this.isLoading = false),
    });
  }
}
