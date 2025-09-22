import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { HttpModule } from '@nestjs/axios';
import { DataLineageService } from './data-lineage.service';
import { DataClassificationService } from './data-classification.service';
import { AuditModule } from '../audit/audit.module';

@Module({
  imports: [
    ConfigModule,
    HttpModule,
    AuditModule,
  ],
  providers: [
    DataLineageService,
    DataClassificationService,
  ],
  exports: [
    DataLineageService,
    DataClassificationService,
  ],
})
export class DataGovernanceModule {}