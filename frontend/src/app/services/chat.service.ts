import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  // 🔹 Backend API URL
  private apiUrl = 'http://localhost:8000/chat';

  constructor(private http: HttpClient) {}

  // 🔹 Send message to backend
  sendMessage(message: string, role: string): Observable<any> {
    const payload = {
      message: message,
      role: role
    };

    return this.http.post<any>(this.apiUrl, payload)
      .pipe(
        catchError(this.handleError)
      );
  }

  // 🔹 Error handling (important for debugging)
  private handleError(error: HttpErrorResponse) {
    console.error('API Error:', error);

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      console.error('Client Error:', error.error.message);
    } else {
      // Backend error
      console.error(`Server Error Code: ${error.status}`);
      console.error('Response:', error.error);
    }

    return throwError(() => new Error('Something went wrong. Please try again.'));
  }
}