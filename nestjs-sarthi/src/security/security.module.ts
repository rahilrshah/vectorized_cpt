import { Module } from '@nestjs/common';
import { EncryptionService } from './encryption.service';
import { PhiProtectionService } from './phi-protection.service';

@Module({
  providers: [EncryptionService, PhiProtectionService],
  exports: [EncryptionService, PhiProtectionService],
})
export class SecurityModule {}