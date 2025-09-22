import { Injectable, Logger, OnApplicationShutdown } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { GatewayService } from './gateway.service';

@Injectable()
export class ServiceRegistrationService implements OnApplicationShutdown {
  private readonly logger = new Logger(ServiceRegistrationService.name);
  private registrationRetryCount = 0;
  private readonly maxRetries = 5;

  constructor(
    private readonly gatewayService: GatewayService,
    private readonly configService: ConfigService,
  ) {}

  async registerService(): Promise<void> {
    const maxRetries = this.maxRetries;
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        await this.gatewayService.registerWithGateway();
        this.registrationRetryCount = 0; // Reset on success
        return;
      } catch (error) {
        attempt++;
        this.registrationRetryCount = attempt;
        
        this.logger.warn(`Service registration attempt ${attempt}/${maxRetries} failed`, {
          error: error.message,
          nextRetryIn: this.getRetryDelay(attempt),
        });

        if (attempt < maxRetries) {
          await this.delay(this.getRetryDelay(attempt));
        } else {
          this.logger.error('Service registration failed after maximum retries', {
            attempts: maxRetries,
            lastError: error.message,
          });
          
          // Continue without gateway registration in development
          if (this.configService.get('NODE_ENV') === 'development') {
            this.logger.warn('Continuing without gateway registration in development mode');
            return;
          }
          
          throw new Error(`Failed to register service after ${maxRetries} attempts`);
        }
      }
    }
  }

  async onApplicationShutdown(signal?: string): Promise<void> {
    this.logger.log('Application shutting down, deregistering from gateway', { signal });
    
    try {
      await this.gatewayService.deregisterFromGateway();
    } catch (error) {
      this.logger.error('Failed to deregister from gateway during shutdown', {
        error: error.message,
      });
    }
  }

  private getRetryDelay(attempt: number): number {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    return Math.min(1000 * Math.pow(2, attempt - 1), 30000);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getRegistrationStatus(): {
    isRegistered: boolean;
    retryCount: number;
    maxRetries: number;
    metadata: Record<string, any>;
  } {
    return {
      isRegistered: this.registrationRetryCount === 0,
      retryCount: this.registrationRetryCount,
      maxRetries: this.maxRetries,
      metadata: this.gatewayService.getServiceMetadata(),
    };
  }
}