import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CptSearchController } from './cpt-search.controller';
import { CptSearchService } from './cpt-search.service';
import { CptCode } from '../database/entities/cpt-code.entity';
import { VectorEngineModule } from '../vector-engine/vector-engine.module';
import { SecurityModule } from '../security/security.module';
import { AuditModule } from '../audit/audit.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([CptCode]),
    VectorEngineModule,
    SecurityModule,
    AuditModule,
  ],
  controllers: [CptSearchController],
  providers: [CptSearchService],
  exports: [CptSearchService],
})
export class CptSearchModule {}