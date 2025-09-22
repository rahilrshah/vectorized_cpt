import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { MultiRegionComplianceService } from './multi-region-compliance.service';
import { RegionalDataService } from './regional-data.service';
import { AuditModule } from '../audit/audit.module';

@Module({
  imports: [
    ConfigModule,
    AuditModule,
  ],
  providers: [
    MultiRegionComplianceService,
    RegionalDataService,
  ],
  exports: [
    MultiRegionComplianceService,
    RegionalDataService,
  ],
})
export class ComplianceModule {}