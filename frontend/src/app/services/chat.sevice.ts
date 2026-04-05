import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

export interface ChatResponse {
  reply: string;
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private apiUrl = 'http://127.0.0.1:8000/api/route/chat';

  constructor(private http: HttpClient) {}

  send(
    message: string,
    userRole: string,
    sessionId: string,
  ): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(this.apiUrl, {
      message,

      user_role: userRole,

      session_id: sessionId,
    });
  }

  uploadResume(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<any>(
      'http://127.0.0.1:8000/resume/upload-and-parse',
      formData,
    );
  }
}
