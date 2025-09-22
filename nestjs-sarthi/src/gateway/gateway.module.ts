import { Module } from '@nestjs/common';
import { GatewayService } from './gateway.service';
import { ServiceRegistrationService } from './service-registration.service';

@Module({
  providers: [GatewayService, ServiceRegistrationService],
  exports: [GatewayService, ServiceRegistrationService],
})
export class GatewayModule {}