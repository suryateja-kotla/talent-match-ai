import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApplicationService {

//   private apiUrl = 'http://localhost:8000/api/applications';

  constructor(private http: HttpClient) {}

getApplications(candidateId: number) {
  return this.http.get(`http://localhost:8000/api/applications/${candidateId}`);
}
}