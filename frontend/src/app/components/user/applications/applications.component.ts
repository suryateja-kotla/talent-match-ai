import {
  Component,
  OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { JobService } from '../../../services/job.service';

interface ApplicationResponse {
  applications: any[];
}

@Component({
  selector: 'app-applications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './applications.component.html',
  styleUrls: ['./applications.component.scss'],
})
export class ApplicationsComponent implements  OnInit {
  applications: any[] = [];

  constructor(private jobService: JobService) {}
  ngOnInit() {
    this.loadApplications();

    this.jobService.refreshApplications$.subscribe(() => {
      this.loadApplications();
    });
  }

  loadApplications() {
    this.jobService.getApplications().subscribe((res: ApplicationResponse) => {
      this.applications = res.applications || [];
    });
  }
}
