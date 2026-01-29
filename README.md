# PYGAME
https://github.com/nicolepas/PYGAME.git

ECO é um jogo de exploração e sobrevivência ambientado em um mundo dominado pela escuridão. Nesse cenário, a visão é limitada e o jogador precisa usar pulsos de luz para revelar temporariamente o ambiente ao seu redor.
Ao emitir um eco de luz, ondas luminosas se expandem pelo cenário, iluminando inimigos e itens por um curto período de tempo. Porém, cada pulso emitido deixa um rastro visível que pode atrair inimigos, tornando cada decisão um risco.
O jogador deve escolher com cuidado quando iluminar e quando permanecer oculto, equilibrando informação e perigo.

### Como o jogo funciona?
O jogador se movimenta em um ambiente escuro.
Ao pressionar ESPAÇO, o personagem emite um pulso de luz que:
- revela inimigos próximos,
- ilumina itens escondidos,
- torna visíveis partes do cenário por alguns segundos.
O pulso de luz tem um tempo de recarga.
Pulsos consecutivos aumentam a agressividade dos inimigos.
O jogador possui um número limitado de vidas e um breve período de invulnerabilidade após sofrer dano.
O objetivo é coletar o máximo de itens possível antes de ser derrotado.

### Inimigos:
Os inimigos reagem à luz, não ao som:
- Patrulha: circulam pela área sem saber da presença do jogador.
- Investigação: se aproximam da última área iluminada.
- Perseguição: após muitos pulsos de luz, passam a caçar o jogador ativamente.
- Os inimigos só podem ser vistos quando são iluminados, reforçando a sensação de tensão e incerteza.

### Objetivo:
Explorar o ambiente escuro, coletar itens e sobreviver usando a luz de forma estratégica.
Iluminar demais revela o caminho — mas também revela você.


### Controles:
WASD / Setas — mover o personagem
ESPAÇO — emitir pulso de luz
ENTER — iniciar ou reiniciar o jogo
ESC — voltar ao menu

### Ideia central:
Em ECO, a luz é sua única aliada — e também o seu maior perigo.
O jogo desafia o jogador a usar a iluminação de forma inteligente, transformando a luz em uma ferramenta estratégica, e não apenas visual.


### Referências:
- Utilizamos a própria pasta da diciplina  (https://insper.github.io/DesignDeSoftware/pygame/handout/)
- Também usamos o ChatGPT para nos auxiliar em erros pontuais e em algumas partes do projeto (as partes que houveram maior auxílio do IA foram comentadas)
- https://www-geeksforgeeks-org.translate.goog/python/pygame-tutorial/?_x_tr_sl=en&_x_tr_tl=pt&_x_tr_hl=pt&_x_tr_pto=tc&_x_tr_hist=true
- https://www-pygame-org.translate.goog/docs/tut/newbieguide.html?_x_tr_sl=en&_x_tr_tl=pt&_x_tr_hl=pt&_x_tr_pto=tc
