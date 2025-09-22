import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AIGovernanceService } from './ai-governance.service';
import { ExplainabilityService } from './explainability.service';
import { AuditModule } from '../audit/audit.module';

@Module({
  imports: [
    ConfigModule,
    AuditModule,
  ],
  providers: [
    AIGovernanceService,
    ExplainabilityService,
  ],
  exports: [
    AIGovernanceService,
    ExplainabilityService,
  ],
})
export class AIGovernanceModule {}