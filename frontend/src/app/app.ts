import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MatSlideToggle } from '@angular/material/slide-toggle';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, MatSlideToggle],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected title = 'delta-erp';
}
