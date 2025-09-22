import { Module } from '@nestjs/common';
import { MetricsService } from './metrics.service';
import { MetricsController } from './metrics.controller';
import { TracingService } from './tracing.service';

@Module({
  providers: [MetricsService, TracingService],
  controllers: [MetricsController],
  exports: [MetricsService, TracingService],
})
export class MonitoringModule {}