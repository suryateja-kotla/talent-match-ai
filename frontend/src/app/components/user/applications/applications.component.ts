import {
  Component,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
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
export class ApplicationsComponent implements OnChanges, OnInit {
  @Input() candidateId: number | null = null;

  applications: any[] = [];

  constructor(private jobService: JobService) {}
  ngOnInit() {
  this.jobService.refreshApplications$.subscribe(() => {
    this.loadApplications();
  });
}
  ngOnChanges(changes: SimpleChanges) {
    if (changes['candidateId'] && this.candidateId !== null) {
      this.loadApplications();
    }
  }

  loadApplications() {
    if (this.candidateId === null) return;
    this.jobService
      .getApplications(this.candidateId)
      .subscribe((res: ApplicationResponse) => {
        this.applications = res.applications;
      });
  }
}
