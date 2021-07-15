import logging

try:
    import torch
    from transformers import pipeline
except ImportError:
    # No installation required if not using this function
    pass

from nlpaug.model.lang_models import LanguageModels


class TextGenTransformers(LanguageModels):
    def __init__(self, model_path='gpt2', device='cuda', min_length=100, max_length=300, 
        batch_size=32, temperature=1.0, top_k=50, top_p=0.9, silence=True):
        super().__init__(device, model_type=None, silence=silence)
        try:
            from transformers import pipeline
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Missed transformers library. Install transfomers by `pip install transformers`')

        self.min_length = min_length
        self.max_length = max_length
        self.batch_size = batch_size
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.model_path = model_path
        if silence:
            # Transformers thrown an warning regrading to weight initialization. It is expected
            orig_log_level = logging.getLogger('transformers.' + 'modeling_utils').getEffectiveLevel()
            logging.getLogger('transformers.' + 'modeling_utils').setLevel(logging.ERROR)

            device = self.convert_device(device)

            self.model = pipeline("text-generation", model=model_path, device=device)
            logging.getLogger('transformers.' + 'modeling_utils').setLevel(orig_log_level)

    def to(self, device):
        self.model.model.to(device)

    def get_device(self):
        return str(self.model.device)

    # def get_tokenizer(self):
    #     return self.model.tokenizer

    # def get_model(self):
    #     return self.model.model

    # def get_max_num_token(self):
    #     return self.model.model.config.max_position_embeddings - 2 * 5

    # def is_skip_candidate(self, candidate):
    #     return candidate.startswith(self.get_subword_prefix())

    # def token2id(self, token):
    #     # Iseue 181: TokenizerFast have convert_tokens_to_ids but not convert_tokens_to_id
    #     if 'TokenizerFast' in self.tokenizer.__class__.__name__:
    #         # New transformers API
    #         return self.model.tokenizer.convert_tokens_to_ids(token)
    #     else:
    #         # Old transformers API
    #         return self.model.tokenizer._convert_token_to_id(token)

    # def id2token(self, _id):
    #     return self.model.tokenizer._convert_id_to_token(_id)

    def predict(self, texts, target_words=None, n=1):
        results = []
        with torch.no_grad():
            for i in range(0, len(texts), self.batch_size):
                predict_result = self.model(
                    texts[i:i+self.batch_size], 
                    pad_token_id=50256,
                    min_length=self.min_length, 
                    max_length=self.max_length,
                    temperature=self.temperature,
                    top_k=self.top_k,
                    top_p=self.top_p,
                    do_sample=True,
                    num_return_sequences=1,
                )
                if isinstance(predict_result, list):
                    if len(predict_result) > 1:
                        results.extend([y for x in predict_result for y in x])
                    elif len(predict_result) == 1:
                        results.extend(predict_result)

        return [r['generated_text'] for r in results]
