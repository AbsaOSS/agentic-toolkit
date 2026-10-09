import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { SearchComponent } from './search/search.component';
import { RumService } from './services/rum.service';

@NgModule({
  declarations: [AppComponent, SearchComponent],
  imports: [BrowserModule, AppRoutingModule],
  providers: [
    {
      provide: APP_INITIALIZER,
      useFactory: (rum: RumService) => () => rum.init(),
      deps: [RumService],
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
